## Build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

## Production stage
FROM nginx:stable-alpine
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx config inline to avoid copy issues
RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
  listen 80;
  server_name  localhost;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }
}
EOF

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
