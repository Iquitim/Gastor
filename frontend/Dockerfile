# Estágio de Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
# A variável de ambiente precisa ser definida no build para estáticos
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm run build

# Estágio de Servidor (Nginx)
FROM nginx:alpine
# Copia os arquivos estáticos gerados (out) para o diretório do Nginx
COPY --from=builder /app/out /usr/share/nginx/html
# Configuração básica do Nginx para lidar com rotas do React (SPA)
RUN echo 'server { \
    listen 80; \
    location / { \
    root /usr/share/nginx/html; \
    index index.html index.htm; \
    try_files $uri $uri/ /index.html; \
    } \
    }' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
