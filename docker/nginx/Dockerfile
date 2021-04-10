FROM nginx:1.19.0-alpine

# Create user account
RUN addgroup -S inventreegroup && adduser -S inventree -G inventreegroup

ENV HOME=/home/inventree
WORKDIR $HOME

# Create the "static" volume directory
RUN mkdir $HOME/static

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d

