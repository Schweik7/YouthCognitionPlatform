阅读流畅性这一块，我们还需要考虑成人的

[ ]麻烦的朗读：小学阅读准确性 （）
测验内容：要求儿童依次朗读每组内的所有汉字，不会可以跳过。
主试记录：读对打勾，读错打叉并记录儿童读错的拼音，不会读打圈。
计分方式：朗读正确计1分，错误或不会计0分，以每组小分乘以每组系数求和得到总分。

[ ]麻烦的朗读：小学朗读流畅性-1min读字 （五个字一组）
测验内容：在1min的倒计时内，让儿童尽快按行朗读字表上的汉字。共朗读两遍，第一遍结束后重新计时朗读第二遍。
主试记录：儿童朗读的同时，在汉字下方的格子内对被试朗读结果进行记录，正确朗读不记录，错误朗读打叉，漏读画圈，用脚标备注错读或漏读发生在第几遍。如×1代表这个字第一遍读错。
计分方式：只记录正确朗读的个数作为分数，错读漏读不计分也不扣分。两遍平均分作为最终得分。

非常棒！接下来让我们开发一个新的功能，叫“朗读流畅性”。在1分钟的倒计时内，让儿童尽快按行朗读字表上的汉字（位于ise-demo/character.txt，每行10个字，共18行）。共朗读两遍，第一遍结束后重新计时朗读第二遍。只记录正确朗读的个数作为分数。当儿童朗读完每行后，

igneous:gg1ag51o5rlur91hp
ipb_member_id:4286824
ipb_pass_hash:7423a7387437ad1b071134c697ad7a59

APPID:e96b71cc
APISecret:YTM0YzkxYTk1MWQzOTdkZDg3Zjg0MTQx
APIKey:c596bae72326e35a645eca27bf9d235a

https://www.xfyun.cn/doc/Ise/IseAPI.html#%E8%AF%95%E9%A2%98%E6%A0%BC%E5%BC%8F%E8%AF%B4%E6%98%8E
中文字（read_syllable） 


read_syllable层级字段说明：
属性	注释
phone_score	声韵分
fluency_score	流畅度分（暂会返回0分）
tone_score	调型分
total_score	总分
beg_pos/end_pos	始末位置（单位：帧，每帧相当于10ms)
content	试卷内容
time_len	时长（单位：帧，每帧相当于10ms）

sentence层级字段说明：
属性	注释
time_len	时长（单位：帧，每帧相当于10ms）
beg_pos/end_pos	始末位置（单位：帧，每帧相当于10ms)
content	试卷内容

word层级字段说明：
属性	注释
beg_pos / end_pos	始末位置（单位：帧，每帧相当于10ms)
symbol	拼音：数字代表声调，5表示轻声
content	试卷内容
time_len	时长（单位：帧，每帧相当于10ms)



syll层级字段说明：
属性	注释
beg_pos / end_pos	始末位置（帧）
dp_message	增漏信息，0(正确）16(漏读）32(增读）64(回读）128(替换）
symbol	拼音：数字代表声调，5表示轻声
content	试卷内容
rec_node_type	paper(试卷内容）,sil(非试卷内容）
time_len	时长（单位：帧，每帧相当于10ms)
phone层级字段说明：

属性	注释
beg_pos / end_pos	始末位置（单位：帧，每帧相当于10ms)
dp_message	增漏信息，0(正确）16(漏读）32(增读）64(回读）128(替换）
content	试卷内容
rec_node_type	paper(试卷内容）,sil(非试卷内容）
perr_msg	错误信息：1(声韵错）2(调型错）3(声韵调型错），当dp_message不为0时，perr_msg可能出现与dp_message值保持一致的情况
time_len	时长（单位：帧，每帧相当于10ms)