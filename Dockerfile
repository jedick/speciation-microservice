# Start with minimal Docker image for R
# https://github.com/r-hub/r-minimal
FROM rhub/r-minimal

# Set working directory
WORKDIR /app

# Single RUN instruction saves space in image and build cache;
# here document (<<EOF) runs multiple commands without chaining them with a
# pipeline operator: https://docs.docker.com/build/building/best-practices/#run
# NOTE: Any change in the here document (including comments!) invalidates the layer cache
RUN <<EOF
# Install CHNOSZ and other packages required by AqEquil,
# keeping compilers around for EQ3/6 and rpy2
installr -a gfortran -c CHNOSZ MASS comprehenr dplyr pracma stringr
# Install Python, pip, virtualenv, and git
apk add --no-cache python3 py3-pip py3-virtualenv git
# Install development libraries required by rpy2
apk add --no-cache pcre2-dev xz-dev bzip2-dev zstd-dev python3-dev
# Install tools required to build awslambdaric
apk add --no-cache cmake autoconf automake libtool binutils
# execinfo is needed for awslambdaric
# https://github.com/zolll23/execinfo
git clone https://github.com/zolll23/execinfo
cd execinfo
make
make install
cd ..
rm -rf execinfo
# Download and install EQ3/6
git clone https://github.com/39alpha/eq3_6
cd eq3_6
make
# Patch to fix error: realpath: -m: No such file or directory
sed -i s/realpath\ -m/realpath/g test/eq3nr/test.sh
sed -i s/realpath\ -m/realpath/g test/eqpt/test.sh
sed -i s/realpath\ -m/realpath/g test/eq6/test.sh
# NOTE: Python is required for `make test`
# FIXME: test error in eq3nr
#make test
make PREFIX=/opt/eq3_6 install
# Remove EQ3/6 build directory
cd ..
rm -rf eq3_6
# Create and activate virtual environment for installing packages
python3 -m venv /opt/venv
export PATH="/opt/venv/bin:$PATH"
# Install packages within the virtual environment
# Use --no-cache-dir to save space in image
pip --no-cache-dir install AqEquil pyCHNOSZ awslambdaric
# Remove compiler packages
apk del gcc g++ gfortran musl-dev
apk del cmake autoconf automake libtool binutils
# Download thermodynamic database
git clone https://github.com/worm-portal/WORM-db
EOF

# Export the location of the R shared library
# See https://github.com/rpy2/rpy2
ENV LD_LIBRARY_PATH=/usr/local/lib/R/lib:/usr/lib
# Activate virtual environment for running the app
ENV PATH="/opt/venv/bin:$PATH"
# Directory with EQ3/6 executables
ENV EQ36CO="/opt/eq3_6/bin"
# Directory with thermodynamic data files (must be absolute path)
ENV EQ36DA="/app/WORM-db"

# (Optional) Add Lambda Runtime Interface Emulator and use a script in the ENTRYPOINT for simpler local runs
ADD https://github.com/aws/aws-lambda-runtime-interface-emulator/releases/latest/download/aws-lambda-rie /usr/bin/aws-lambda-rie
COPY entry.sh /
RUN chmod 755 /usr/bin/aws-lambda-rie /entry.sh

# Copy app files last so they can be updated easily
COPY ./app.py /app

# Set runtime interface client as default command for the container runtime
#ENTRYPOINT [ "python", "-m", "awslambdaric" ]
ENTRYPOINT [ "/entry.sh" ]
# Pass the name of the function handler as an argument to the runtime
CMD [ "app.handler" ]
