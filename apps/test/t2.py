# Dataパケットの送信
import cefpyco

with cefpyco.create_handle() ashandle: 
  # ccn:/testというコンテンツ名・チャンク番号0で
  # helloというテキストコンテンツをDataパケットとして送信
  handle.send_data("ccn:/test", "hello", 0)
