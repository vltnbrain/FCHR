# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Install deps
COPY package.json package-lock.json* pnpm-lock.yaml* yarn.lock* ./
RUN if [ -f package-lock.json ]; then npm ci; \
    elif [ -f yarn.lock ]; then yarn install --frozen-lockfile; \
    elif [ -f pnpm-lock.yaml ]; then npm i -g pnpm && pnpm i --frozen-lockfile; \
    else npm install; fi

# Copy sources
COPY . .

# Build with Vite env vars supplied as build args
ARG VITE_API_BASE_URL
ARG VITE_GEMINI_API_KEY
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
ENV VITE_GEMINI_API_KEY=${VITE_GEMINI_API_KEY}
RUN npm run build

# Runtime stage using a simple static server
FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm i -g serve
ENV PORT=8080
EXPOSE 8080
CMD ["serve", "-s", "dist", "-l", "0.0.0.0:$PORT"]

