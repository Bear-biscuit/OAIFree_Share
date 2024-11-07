## 项目介绍  
基于始皇的OAIFree服务，搭建一个共享站，方便给自己的小伙伴们使用  

## 配置项  

请修改<kbd>instance\config.py</kbd>文件中的相关配置

关于邮箱部分，使用的是[cloudflare_temp_email](https://github.com/dreamhunter2333/cloudflare_temp_email)项目，请根据作者的部署教程进行部署(非必需)

## 部署 

1、克隆项目  

2、安装```MySQL```

3、运行```init_db.sql```创建数据库和表

4、修改<kbd>instance\config.py</kbd>文件中的配置信息 

5、安装依赖```pip install -r requirements.txt```

6、在项目目录运行```python run.py```

7、如果看到一下字样，就代表运行成功  
```
在主进程中初始化自动刷新, 当前时间: 2024-11-07 13:05:04.351826
设置初始定时器, 延迟秒数: 250715.195757
 * Serving Flask app 'run.py'
 * Debug mode: off
WARNING: This is a development server. Do not use it in a production deployment. Use a production WSGI server instead.
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.18.0.3:5000
Press CTRL+C to quit
```

8、使用ip:端口访问  
默认管理员账号  
```
admin  123123
```



