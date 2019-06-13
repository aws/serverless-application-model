package main

import (
	"bytes"
	"github.com/aws/aws-lambda-go/events"
	"github.com/aws/aws-lambda-go/lambda"
	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/s3"
	"github.com/aws/aws-sdk-go/service/s3/s3manager"
	"github.com/nfnt/resize"
	"image"
	"image/jpeg"
	"log"
	"os"
)

func Handler(event events.S3Event) (string, error) {
	dstBucket := os.Getenv("DestBucket")
	svc := s3.New(session.New())
	downloader := s3manager.NewDownloaderWithClient(svc)
	uploader := s3manager.NewUploaderWithClient(svc)

	for _, record := range event.Records {
		srcBucket := record.S3.Bucket.Name
		srcKey := record.S3.Object.Key
		imgSize := record.S3.Object.Size

		file := make([]byte, imgSize)
		_, err := downloader.Download(aws.NewWriteAtBuffer(file),
			&s3.GetObjectInput{
				Bucket: aws.String(srcBucket),
				Key:    aws.String(srcKey),
			})
		if err != nil {
			log.Fatalln("Donwload error:  " + err.Error())
		}

		reader := bytes.NewReader(file)
		img, _, err := image.Decode(reader)
		if err != nil {
			log.Fatalln("Decode error: " + err.Error())
		}

		resizedImg := resize.Resize(300, 0, img, resize.Lanczos3)

		buf := new(bytes.Buffer)
		err = jpeg.Encode(buf, resizedImg, &jpeg.Options{
			Quality: 50,
		})
		if err != nil {
			log.Fatalln("Encode error: " + err.Error())
		}

		imgBody := bytes.NewReader(buf.Bytes())

		_, err = uploader.Upload(&s3manager.UploadInput{
			Bucket: aws.String(dstBucket),
			Key:    aws.String(srcKey),
			Body:   imgBody,
		})
		if err != nil {
			log.Fatalln("Upload error: " + err.Error())
		}
	}

	return "Resize successful", nil
}

func main() {
	lambda.Start(Handler)
}
