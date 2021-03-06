# 基于容器的后端服务架构

> 在探索kubernetes的应用时，调研了几个gateway，发现fabio支持发现服务，自动生成路由，结合consul，registrator, 可以很容易的部署一套服务，比较轻量，很容易玩起来。

结构大致为：


## Start Consul

安装 consul, 如果检测到多个 private ip, 会报错，可以用 -advertise 指定一个ip.
```
// config.json , 指定 DNS port
{
    "recursors" : [ "8.8.8.8" ],
    "ports" : {
        "dns" : 53
    }
}

sudo docker run -d --name=consul --net=host -v $PWD/config.json:/config/config.json gliderlabs/consul-server -bootstrap -advertise=172.28.128.3 

curl 172.28.128.3:8500/v1/catalog/services
```

## Start Registrator

启动 registrator, 因为需要调用docker api， 所以需要把docker.sock 映射到容器内部，如果你使用了tcp， 那么需要设置对应的url。 

如果你希望上报容器内部ip:port, 那么需要在启动参数中加入 `-internal=true`, 这样注册的 Service, 都是容器内部的ip, 而port对于同一个service而言，一般是固定的，例如 一个hello服务的两个实例分别为 10.10.1.12:9090, 10.10.1.13:9090. 这样的话，就需要配置一个容器跨host的网络方案，例如 flannel, 等。 可以参考上一篇 [Flannel with Docker](https://segmentfault.com/a/1190000007585313)

为了简便测试，这里就不配置flannel了。`-ip`是指定注册service时候使用的ip，建议要指定，选取当前机器的内网 private ip即可。我这里是 `172.28.128.3`.

```
sudo docker run -d --name=registrator --volume=/var/run/docker.sock:/tmp/docker.sock gliderlabs/registrator:latest -ip=172.28.128.3 consul://172.28.128.3:8500 
```

## Start service

启动服务，这里需要注意的是这些环境变量，作用是 override Registrator的默认值，见名知意，在 registrator 文档中有详细介绍。例如 `SERVICE_9090_NAME` 就是指 端口为 9090 的service 的 name。

需要注意的是 tags 这个字段，`urlprefix-/foo,hello`, 这里 `urlprefix-` 是 gateway 的一种配置，意思为 把访问 /foo 为前缀的请求转发到当前应用来。他能够匹配到例如 `/foo/bar`, `footest`, 等。如果你想加上域名的限制，可以这样 `urlprefix-mysite.com/foo`。 后面还有一个 `hello`, 作用是给这个service打一个标记，可以用作查询用。

```
sudo docker run -d -P -e SERVICE_9090_CHECK_HTTP=/foo/healthcheck -e SERVICE_9090_NAME=hello -e SERVICE_CHECK_INTERVAL=10s -e SERVICE_CHECK_TIMEOUT=5s -e SERVICE_TAGS=urlprefix-/foo,hello silentred/alpine-hello:v2

curl 172.28.128.3:8500/v1/catalog/services
//现在应该能看到刚启动的hello服务了
{"consul":[],"hello":["urlprefix-mysite.com/foo","hello","urlprefix-/foo"]}
```

测试 DNS
```
sudo yum install bind-utils
dig @172.28.128.3 hello.service.consul SRV
```

可以设置 /etc/resolv.conf
```
nameserver 172.28.128.3
search service.consul
```
这样无论在容器内部，还是外部都可以直接解析 sevice 名， 例如：
```
[vagrant@localhost ~]$ ping hello
PING hello.service.consul (172.28.128.3) 56(84) bytes of data.
64 bytes from localhost.localdomain.node.dc1.consul (172.28.128.3): icmp_seq=1 ttl=64 time=0.016 ms

[vagrant@localhost ~]$ sudo docker exec -it fdde1b8247b8 bash
bash-4.4# ping hello
PING hello (172.28.128.6): 56 data bytes
64 bytes from 172.28.128.6: seq=0 ttl=63 time=0.361 ms
```

## Start Gateway

前端Gateway 根据 consul中注册的 service，生成对应的路由规则，把流量分发到各个节点。 这个项目还有一个 ui 管理 route信息，端口为 9998。

创建一个配置文件 fabio.properties
```
registry.consul.addr = 172.28.128.3:8500
```
在当前目录运行
```
docker run -d -p 9999:9999 -p 9998:9998 -v $PWD/fabio.properties:/etc/fabio/fabio.properties magiconair/fabio
```

测试gateway:
```
curl 172.28.128.3:9999/foo/bar
```


## Health Check

```
sudo ifdown eth1

curl http://localhost:8500/v1/health/state/critical

[
    {
        "Node":"localhost.localdomain",
        "CheckID":"service:afa2769cd049:loving_shannon:9090",
        "Name":"Service 'hello' check",
        "Status":"critical",
        "Notes":"",
        "Output":"Get http://172.28.128.6:32768/foo/healthcheck: net/http: request canceled while waiting for connection (Client.Timeout exceeded while awaiting headers)",
        "ServiceID":"afa2769cd049:loving_shannon:9090",
        "ServiceName":"hello",
        "CreateIndex":379,
        "ModifyIndex":457
    }
]

sudo ifup eth1
```

在启动 consul的时候，我们使用了`-ui` 参数，我们可以在 `172.28.128.3:8500/ui` 访问到consul的web ui管理界面，看到各个服务的状态.

## 对比

注册容器外IP：
每个注册的service的port都是变化的，并且因为映射内部port到了host，外部可以随意访问，私密性较弱。

注册容器内IP：
每个注册的service的port都是固定的，只能从容器内部访问。如果用 flannel，可能有一些性能损失。

## DNS服务发现

查了一下如何利用DNS SRV类型来发现服务。本来以为可以用类似 `Dial("hello", SRV)` 的魔法 (我们都是膜法师，+1s), 查了一些资料貌似没有这么方便。看了下golang的net包，发现了两个方法 `LookupSRV`, `LookupHost`, 于是测试了一下，看下结果，大家知道该怎么用了吧，嘿嘿。

``` golang
cname, addrs, err := net.LookupSRV("", "", "hello.service.consul")
fmt.Printf("%s, %#v, %s \n", cname, addrs, err)
for _, srv := range addrs {
    fmt.Printf("%#v \n", *srv)
}

newAddrs, err := net.LookupHost("hello.service.consul")
fmt.Printf("%#v, %s \n", newAddrs, err)
```

```
//output
[vagrant@bogon dns]$ go run mx.go
hello.service.consul., []*net.SRV{(*net.SRV)(0xc420010980), (*net.SRV)(0xc4200109a0)}, %!s(<nil>)
net.SRV{Target:"bogon.node.dc1.consul.", Port:0x8003, Priority:0x1, Weight:0x1}
net.SRV{Target:"bogon.node.dc1.consul.", Port:0x8000, Priority:0x1, Weight:0x1}
[]string{"172.28.128.3", "172.28.128.4"}, %!s(<nil>)
```