# serverless-speciation

## Intro: Chemical speciation as an AWS Lambda function

This repo wraps the speciate function from [worm-portal/AqEquil](https://github.com/worm-portal/AqEquil) in a Docker container that can be deployed in AWS Lambda.
This provides a serverless execution environment, meaning that we only need to upload the Docker image without worrying about server administration.

Frontend apps can get speciation results from the AWS Lambda function without needing to install complex dependencies.
See the Jupyter notebook for an example.

## Deploying on AWS

See the [Deployment Notes](deployment-notes.md) for detailed notes on deployment.
The steps here are based on the
AWS Blog for
[New for AWS Lambda – Container Image Support](https://aws.amazon.com/blogs/aws/new-for-aws-lambda-container-image-support/)
and AWS docs for
[Using an alternative base image with the runtime interface client](https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients).


## Local testing

In case you want to build the container and test it locally, follow these steps

Build the container

```sh
docker build -t worm-speciate:latest .
```

Startup container with the runtime interface emulator (built into the image) for local testing.

```sh
docker run -p 9000:8080 worm-speciate:latest
```
