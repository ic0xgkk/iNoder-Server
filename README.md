# iNoder Server

完全取代iNode，客户端无需再安装iNode即可通过认证

每天早上7点05分自动开始批量重认证（先下线，再上线），请确保此时路由器已经插上，否则会报 VLAN绑定检查失败 错误

若计划任务错过，可以手动进入WebUI重连

请确保服务器时区为CST同时时间正确

该系统需要依赖libinoder，不过为了避免法律纠纷此模块暂时不开源。二进制文件后边有空修完bug再放

只支持H3C的私有Portal认证，并且只写了一部分功能

# 依赖

此工具只支持Linux。

需要Python3.5+ 和 libinoder 两部分

Python3依赖可看代码自行安装