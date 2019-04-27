# pyfuck_h3c

## 简介

最原始的版本。目前已经不再维护

宿舍内专用，用于NAT之后的局域网使用，配合上游RouterOS的设备一起使用，工具会自动获取RouterOS的接口IP完成Portal请求构造

亲测可用

需要依赖libfuckh3c动态链接，暂不开源

## 逻辑

* 启动Flask
* 填入lib到FAPP中
* WebUI线程启动
* 单次认证启动
* 持续性网络检查启动（lib中）

后续WebUI操作由FApp启动lib相应方法
