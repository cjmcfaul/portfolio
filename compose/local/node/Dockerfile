FROM node:22-bullseye-slim

WORKDIR /app/frontend

COPY ./frontend/package.json /app/frontend

RUN npm install && npm cache clean --force

ENV PATH ./frontend/node_modules/.bin/:$PATH
