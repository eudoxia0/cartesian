#!/usr/bin/env bash

cd frontend
npm run build
cd ..
rm -rf server/theatre/static
mkdir server/theatre/static
cp -a frontend/build/static/. server/theatre/static
mv frontend/build/static/css/main.*.css server/theatre/static/bundle.css
mv frontend/build/static/js/main.*.js server/theatre/static/bundle.js