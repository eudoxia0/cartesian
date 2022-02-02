#!/usr/bin/env bash

cd frontend
npm run build
cd ..
rm -rf server/theatre/static
mkdir server/theatre/static
cp -a frontend/build/. server/theatre/static
mv server/theatre/static/static/css/main.*.css server/theatre/static/bundle.css
mv server/theatre/static/static/js/main.*.js server/theatre/static/bundle.js