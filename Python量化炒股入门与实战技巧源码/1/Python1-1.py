n = 12              #定义整型变量，设置绘制等腰三角的¤个数
i = 0               #用来统计循环次数
while i < n:
    #内容由二部分组成，空格和※符号
    #空格一开始很多，是2×（总行数 - 当前行数），然后越来越少
    #¤的个数与行号的关系 ： ¤个数 = 当前行号 × 2 + 1
    print("%s%s" % ("  "*(n - i), "¤"*(i * 2 + 1))) 
    i += 1
