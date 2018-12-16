# bookmark_checker
* 说明：
  出于自己想要验证大量书签是否可访问，但是没有找到好用的插件/软件，所以用python写的验证脚本
  
* python3
* python库：
  * Requests
  * BeautifulSoup

# 使用方法：
  1. 首先使用chrome书签管理器导出书签为html文件
  2. 修改脚本中的localpath参数为上述html文件的路径
  3. 运行python脚本
  
# To-do:
  - [x] 多线程实现，加快验证速度
  - [ ] 增加头部，减少网站误伤

