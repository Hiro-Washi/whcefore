import cefpyco 
with cefpyco.create_handle() as handle: 
  # ccn:/testというコンテンツの0番目のチャンクを
  # 要求するInterestパケットを送信
  handle.send_interest("ccn:/test", 0)
