import json
import boto3
from io import BytesIO
import zipfile
import mimetypes

def lambda_handler(event, context):

    s3 = boto3.resource('s3')
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:853693707439:deploymentPortfolioTopic')
    location = {
        "bucketName": 'potfoliobuilddev.chimata.info',
        "objectKey": 'portfoliobuild.zip'
    }
    try:
        job = event.get("CodePipeline.job")

        for artifact in job["data"]["inputArtifacts"]:
            print(artifact["name"])
            if artifact["name"] == "BuildArtifact":
                location = artifact["location"]["s3Location"]
        print("Building portfolio from "+str(location))
        portfolio_bucket = s3.Bucket('babu.chimata.info')
        build_bucket = s3.Bucket(location["bucketName"])
        portfolio_zip = BytesIO()
        build_bucket.download_fileobj(location["objectKey"],portfolio_zip)
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)

                portfolio_bucket.upload_fileobj(obj,nm,
                ExtraArgs={'ContentType':mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
                topic.publish(Subject="Portfolio Deployed", Message="Portfolio deployed successfully")

                if job:
                    codepipeline = boto3.client('codepipeline')
                    codepipeline.put_job_success_result(jobId=job["id"])
    except:
        topic.publish(Subject="Portfolio deployment Failed", Message="Portfolio deployment failed")
        raise
    return 'Hello from Lambda!'
