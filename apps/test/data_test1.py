# Dataパケットの送信
import cefpyco

with cefpyco.create_handle() as handle: 
  # ccn:/testというコンテンツ名・チャンク番号0で
  # helloというテキストコンテンツをDataパケットとして送信
  print("send data")
  handle.send_data("ccnx:/test/data", "hello", 0)
  print("done: send data")
