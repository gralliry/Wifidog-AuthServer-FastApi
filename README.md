# Wifidog-Server-FastApi

```
# nginx配置，因为本程序的session是基于cookies加密实现的，cookies的数据量会很大
# nginx对headers大小有限制
server
{
    ...
    # 增加默认请求头部缓冲区大小
    client_header_buffer_size 16k;
    # 增加允许的请求头部缓冲区数量
    large_client_header_buffers 4 16k;
    ...
}
```

