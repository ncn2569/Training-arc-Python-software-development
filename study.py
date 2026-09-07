class Solution(object):
    def moveZeroes(self, nums):
        """
        :type nums: List[int]
        :rtype: None Do not return anything, modify nums in-place instead.
        """

        if len(nums) == 1 or len(nums) == 0:
            return nums
        for i in range(len(nums) - 1):
            if nums[i] == 0:
                temp = nums[i]
                for idx2 in range(i,len(nums)):
                    # print(nums,i,idx2)
                    if nums[idx2] != 0:
                        nums[i] = nums[idx2]
                        nums[idx2] = temp
                        break
        return nums


if __name__ == "__main__":
    sol = Solution()
    nums = [0, 1, 0, 3, 12]
    print(sol.moveZeroes(nums))
    print(list(range(1,4)))
    print(list(range(4)))