import logging
class Solution(object):
    

        
if __name__ == "__main__":
    logging.basicConfig(level = logging.INFO)
    sol = Solution()
    res = sol.firstBadVersion(n=2126753390)
    logging.info(f"Số đầu tiên bad là:  {res}")
    logging.info(f"Số lần gọi hàm isBadVersion:  {sol.count}")