def handle_postback_event(event):
    if event.postback.data == 'postback':
        print('Postback event is triggered')
    # TODO: 之後依 data 內容分派到不同模組（例如景點詳情、文化 Quiz 選項等）