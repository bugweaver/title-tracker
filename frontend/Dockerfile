FROM oven/bun:latest

WORKDIR /app

COPY package.json bun.lock ./

RUN bun install

COPY . .

ARG VITE_API_URL=/api/v1
ARG VITE_DISABLE_DEVTOOLS=true

RUN VITE_API_URL="$VITE_API_URL" VITE_DISABLE_DEVTOOLS="$VITE_DISABLE_DEVTOOLS" bun run build

EXPOSE 5173

CMD ["bun", "run", "preview", "--", "--host", "0.0.0.0", "--port", "5173"]
