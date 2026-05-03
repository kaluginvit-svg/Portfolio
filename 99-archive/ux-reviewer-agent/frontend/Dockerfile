# Фронтенд в режиме разработки: npm install + npm run dev
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .
EXPOSE 3000
# npx держит процесс в foreground
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "3000"]
