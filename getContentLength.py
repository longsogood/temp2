import boto3

def get_s3_file_size(bucket_name: str, key: str) -> int:
    """
    Trả về kích thước file trên S3 tính bằng byte.
    """
    s3 = boto3.client('s3')
    response = s3.head_object(Bucket=bucket_name, Key=key)
    return response['ContentLength']

# Ví dụ sử dụng:
size = get_s3_file_size("ten-bucket", "duong_dan/ten_file.txt")
print(f"Kích thước file trên S3: {size} bytes")
