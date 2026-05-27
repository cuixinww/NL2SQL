# 基础镜像：使用你提供的 DaoCloud 国内加速地址（8.19.10）
FROM m.daocloud.io/docker.elastic.co/elasticsearch/elasticsearch:8.19.10

# 切换 root 权限安装插件
USER root

# 复制本地已经下载好的 IK 插件到容器内
COPY plugins/elasticsearch-analysis-ik-8.19.10.zip /tmp/

# 离线安装 IK 分词插件（版本完全匹配）
RUN /usr/share/elasticsearch/bin/elasticsearch-plugin install --batch \
    file:///tmp/elasticsearch-analysis-ik-8.19.10.zip

# 修复插件目录权限（ES 必须用 elasticsearch 用户权限）
RUN chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/plugins

# 切换回默认用户，保证安全运行
USER elasticsearch