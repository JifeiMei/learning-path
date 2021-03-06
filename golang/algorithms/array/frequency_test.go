package array

import (
	"fmt"
	"testing"
)

func TestFrequency(t *testing.T) {
	slice := []int{2, 3, 3, 2, 5}

	slice = count(slice)

	for i := 0; i < len(slice); i++ {
		fmt.Printf("num %d shows %d times \n", i+1, slice[i])
	}

}

func TestBSearch(t *testing.T) {
	slice := []int{1, 2, 3, 4, 5, 6}
	res := bSearch(slice, 6)
	fmt.Println(res)
}

func TestFib(t *testing.T) {
	fmt.Println(fib(10))
}

func TestNonRepeating(t *testing.T) {
	firstNonRepeating("ABCDEFGHIJKLADTVDERFSWVGHQWCNOPENSMSJWIERTFB")
	firstNonRepeatingOptimized("ABCDEFGHIJKLADTVDERFSWVGHQWCNOPENSMSJWIERTFB")
}

func TestRearrange(t *testing.T) {
	s := []int{-2, -3, -4, -5, -1, 3, 2, 4, 5, -6, 7, -9, 9, 10, 11, -10, -11}
	fmt.Println(rearrangeNaive(s))
	reArrange(s)
	fmt.Println(s)
}

func TestNextGreaterSameDigits(t *testing.T) {
	s := []int{6, 9, 3, 8, 6, 5, 2}
	nextGreaterWithSameDigits(s)
	fmt.Println(s)
}

func TestMedian(t *testing.T) {
	a := []int{1, 3, 5, 11, 17}
	b := []int{9, 10, 11, 13, 14}

	fmt.Println(findMedian(a, b))
}

func TestLongestSubStr(t *testing.T) {
	//ABCDBBBABDEFGCABD
	fmt.Println(longestNonRepeatingSubstr("AAAAAABCDBABDEFGCABD"))
}
