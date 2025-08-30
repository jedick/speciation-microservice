# Deploying worm-speciate Docker container on AWS Lambda

1. Create a repository in Amazon ECR using the create-repository command.

```sh
aws ecr create-repository --repository-name worm-speciate --region us-east-2 --image-scanning-configuration scanOnPush=true --image-tag-mutability MUTABLE
```

- Result (111222333444 is a fake Account ID):

```
"repositoryUri": "111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate",
```

2. Run the docker tag command to tag your local image into your Amazon ECR repository as the latest version.

Make sure to include :latest at the end of the URI.

```sh
docker tag worm-speciate:latest 111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest
```

3. Run the get-login-password command to authenticate the Docker CLI to your Amazon ECR registry.

- NOTE: docker login requires password store - search for docker login pass init.

```sh
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 111222333444.dkr.ecr.us-east-2.amazonaws.com
```

4. Run the docker push command to deploy your local image to the Amazon ECR repository.

- NOTE: Retrieve password so gpg-agent remembers credentials, e.g.:

```sh
pass docker-credential-helpers/<long-id>/AWS > /dev/null
```

```sh
docker push 111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest
```

5. Create an execution role for the function, if you don't already have one. 

- Prereq: Add policy that allows the iam:CreateRole action (name: IAMCreateRole)
- NOTE: After creating the role, add AWSLambdaBasicExecutionRole policy to enable CloudWatch metrics

```sh
aws iam create-role \
  --role-name lambda-ex \
  --assume-role-policy-document '{"Version": "2012-10-17","Statement": [{ "Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]}'
```

- Result:

```
"Arn": "arn:aws:iam::111222333444:role/lambda-ex",
```

6. Create the Lambda function.

- Prereq: Add policy that allows the iam:PassRole action (name: IAMPassRole)

```sh
aws lambda create-function \
  --function-name worm-speciate \
  --package-type Image \
  --code ImageUri=111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest \
  --role arn:aws:iam::111222333444:role/lambda-ex \
  --memory-size 2048 \
  --timeout 60
```

- Result:

```
"State": "Pending",
"StateReason": "The function is being created.",
"StateReasonCode": "Creating",
```

7. Invoke the function using a file as input.

```sh
# Prepare the data: convert CSV to JSON as a single long string
jq -Rs '{input: .}' example.csv > example.json
aws lambda invoke --function-name worm-speciate --cli-binary-format raw-in-base64-out --payload file://example.json lambda_output.txt
```

- First try: "errorMessage":"2025-08-19T08:37:05.400Z Task timed out after 3.03 seconds"

Increase timeout

```sh
aws lambda update-function-configuration --function-name worm-speciate --timeout 60
```

- Second try: "Task timed out after 63.05 seconds"

Increase memory

```sh
aws lambda update-function-configuration --function-name worm-speciate --memory-size 2048
```

- Third try: "Speciation calculation failed: [Errno 30] Read-only file system: 'rxn_3i'"

Use /tmp directory (storage limit of 512 MB) (changes made in app.py)

8. First successful test run

```
Resources configured
    2048 MB
Max memory used
    273 MB
```

9. Updating function

```sh
docker tag worm-speciate:latest 111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest
docker push 111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest
aws lambda update-function-code \
  --function-name worm-speciate \
  --image-uri 111222333444.dkr.ecr.us-east-2.amazonaws.com/worm-speciate:latest
```
