# Openshift routers load testing

Two clusters needed, a target cluster that will be tested and one that will be used to generate the load

## Create the routes

TLS routes will be used as they're the ones that generate more load in the servers. In the target cluster:

```
git clone https://github.com/rporres/http-ci-tests.git
cd http-ci-tests/content/quickstarts/nginx
oc new-project load-tests
for i in $(seq 0 24); do
  oc process -p IDENTIFIER=$i -f server-tls-edge.yaml | oc create -n load-tests -f -
  oc process -p IDENTIFIER=$i -f server-tls-reencrypt.yaml | oc create -n load-tests -f -
done
```

and create a `targets.txt` file:

```
TARGETS=$PWD/targets.txt
oc get -n load-tests routes -o json | jq -r '.items[] | "https://" + .spec["host"]' > $TARGETS
```

## Create the load testing cluster aws secret

It will hold the information to upload result files to S3

```
ACCESS_KEY_ID=xxxx
SECRET_ACCESS_KEY=xxxx
oc new-project load-tests
oc create -n load-tests secret generic aws-s3 \
    --from-literal=access_key_id=$ACCESS_KEY_ID \
    --from-literal=secret_access_key=$SECRET_ACCESS_KEY
```

## Create the load testing target configmaps

They will be used by `mb` to determine how to send requests to the target cluster

```bash
git clone https://github.com/rporres/mb-k8s.git
cd mb-k8s

./utils/build-request-json.sh -f $TARGETS -k 1 -c 1 -d 0 -t > request-file-1ka-1c.json
oc create -n load-tests configmap --from-file=request-file-1ka-1c.json request-file-1ka-1c

./utils/build-request-json.sh -f $TARGETS -k 1 -c 50 -d 0 -t > request-file-1ka-50c.json
oc create -n load-tests configmap --from-file=request-file-1ka-50c.json request-file-1ka-50c

./utils/build-request-json.sh -f $TARGETS -k 10 -c 50 -d 0 -t > request-file-10ka-50c.json
oc create -n load-tests configmap --from-file=request-file-10ka-50c.json request-file-10ka-50c

./utils/build-request-json.sh -f $TARGETS -k 100 -c 50 -d 0 -t > request-file-100ka-50c.json
oc create -n load-tests configmap --from-file=request-file-100ka-50c.json request-file-100ka-50c
```

We don't use more than 50 clients per load server to avoid congestion that could affect in any way to the results, but the experience shows it is a conservative setting for servers like m5.xlarge

## Run the tests

```
git clone https://github.com/rporres/mb-k8s.git
cd mb-k8s
helm install <test-name> helm/mb-k8s -f <values.yaml>
```

where `values.yaml` is one of the files inside [`mb-k8s-values-files`](mb-k8s-values-files)

## Prepare the result files

The result of the tests is uploaded into `s3BucketName`. They have to be downloaded and for those tests that run into multiple servers, sorted into one file, e.g. the results of a test distributed in four servers

```
for i in $(ls 100ka-200c-mb-k8s-*.xz); do
  xz -dc $i
done | sort -t, -k1n,1n | xz > 100ka-200c.xz
```

# Create the plots comparing the different runs

In order to create data files for gnuplot from the result files, a utility script is provided [`create-gnuplot-values-file.py`](utils/create-gnuplot-values-file.py). It will create data files counting request rate, median latencies and error rates. Example gnuplot files can be found in [`gnuplot`](gnuplot) directory
