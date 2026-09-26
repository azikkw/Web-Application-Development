# Assignment 1
**Task:** Containerize a simple web application using Docker.

---

Prerequisits
---
- GIT
- Docker

Setup
---
1 Download the project using:
```
git clone https://github.com/azikkw/Web-Application-Development.git
```
Also you can just downlaod the project using the following [link](https://github.com/azikkw/Web-Application-Development/archive/refs/heads/main.zip).

2 Open project and navigate to `/Assignment-1` folder.

3 Create docker image:
```
docker build -t <image_name> <path_to_app>
```

4 Create docker image:
```
docker run -d -p <port>:80 -t --name <container_name> <image_name>
```
