## Sample container application running Flask

```text
$ docker build . -t localbuild:flask
```

And then run it locally with port 5000 exposed:

```
$ docker run -it -p 5000:5000  localbuild:flask
```
