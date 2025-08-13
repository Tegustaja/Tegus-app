docker build --platform linux/amd64 -t tegus .

read -p 'Docker build hash: ' docker_build_hash
read -p 'Docker tag: for kaursoon/justcook:' docker_tag
docker tag $docker_build_hash kaursoon/justcook:$docker_tag
read -p 'Should we push this? '
docker push kaursoon/justcook:$docker_tag