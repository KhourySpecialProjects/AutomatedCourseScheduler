# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# VITE_* are baked into the static bundle at build time, supplied as build args
# by docker-compose.coolify.yaml (a server checkout has no frontend/.env, so
# args are the only channel). Declared as ARG only, no ENV: a supplied build arg
# reaches `npm run build`, while an unsupplied one stays UNSET so a copied
# frontend/.env still wins — the path `make fe-dev` uses for LOCAL dev.
ARG VITE_AUTH0_DOMAIN
ARG VITE_AUTH0_CLIENT_ID
ARG VITE_AUTH0_AUDIENCE
ARG VITE_API_BASE_URL
RUN npm run build

# Stage 2: Serve
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
