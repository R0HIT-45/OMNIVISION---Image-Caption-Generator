# OmniVision Frontend

FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json bun.lock ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
