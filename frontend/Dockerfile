# uses node
FROM node:20

# app directory
WORKDIR /app

# copy information from package.json
COPY frontend/package*.json ./
# installs all the project's dependecies into node_modules
RUN npm ci

COPY frontend /app

EXPOSE 5173

# Vite dev server listen on 0.0.0.0 so host can reach it
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]