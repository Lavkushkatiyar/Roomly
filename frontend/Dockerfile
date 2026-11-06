FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
COPY roomly/package.json ./roomly/package.json
RUN npm ci

COPY roomly ./roomly

ARG VITE_API_BASE_URL=""
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build --workspace roomly


FROM nginx:alpine AS runtime

COPY --from=build /app/roomly/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
