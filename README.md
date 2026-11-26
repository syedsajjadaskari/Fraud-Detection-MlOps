# Fraud-Detection-MlOps


```
git switch --detach dataset-v1
dvc checkout
```
```
#to retrun the version you were working
git switch - 
dvc checkout
```

```
git branch --show-current
git switch -c stage-7-dagshub

git rm --cached data/transaction.csv

dvc add data/transaction.csv
git add .
git commit -m "sate 7 track found" 
git tag stage7-data-v1

dagshub login
dvc remote add -d dagshub \
> https://dagshub.com/<USERNAME>/Fraud-Detection-MlOps.dvc
dvc remote modify dagshub --local auth basic 
dvc remote modify dagshub --local user USERNAME
dvc remote modify dagshub --local ask_password true
```

```
dvc remote remove dagshub --local
dvc remote remove origin  --local
dvc remote list
```
