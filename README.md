# streaming-service
A python streaming service that runs on a Raspberry Pi. Takes the feed streamed from the video-capture service at TCP Port 5555 and sends the frames to the streaming server. Always uses the latest frame which leads to lower FPS but minimal latency.
