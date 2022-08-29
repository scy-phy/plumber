# Dynamic analysis

This directory contains the code to perform dynamic analysis on OpenSSL 1.1.0g in order to re-identify the vulnerability described in [1].

To reproduce the dynamic analysis, perform the following steps on an ARM-based system:

- Clone the OpenSSL git repository into a new folder called `openssl` within this directory.
  ```
  git clone https://github.com/openssl/openssl.git
  ```
- Change into the new `openssl` directory and checkout tag `OpenSSL_1_1_0g`.
  ```
  cd openssl
  git checkout OpenSSL_1_1_0g
  ```
- Configure and compile OpenSSL. If the configure command fails, apply [this workaround](https://github.com/wazuh/wazuh/issues/4054#issuecomment-553453743) and retry.
  ```
  ./Configure -g linux-aarch64 shared
  make
  cd ..
  ```
- Change into the `victim-bn` directory.
  ```
  cd victim-bn
  ```
- Make sure that all constants at the top of `src/victim-bn.c` match your compiled OpenSSL binary.
- Compile the `victim-bn` binary
  ```
  mkdir build
  cd build
  cmake ..
  make
  cd ../..
  ```
- Change into the `runner` directory.
  ```
  cd runner
  ```
- Check that all constants in `constants.py` match your environment
- Collect access and cache traces (traces will be stored in the newly created directory `runner/results`):
  ```
  python3 ./main.py run
  ```
- Evaluate the collected access and cache traces:
  ```
  python3 ./main.py evaluate
  ```

The `evaluate` command prints the classification for each of the traces. Finally, the last line represents the confusion matrix, as shown in Table 6 in the paper.

[1] Youngjoo Shin, Hyung Chan Kim, Dokeun Kwon, Ji Hoon Jeong, and Junbeom Hur. 2018. Unveiling Hardware-based Data Prefetcher, a Hidden Source of Information Leakage. In Proceedings of the 2018 ACM SIGSAC Conference on Computer and Communications Security (CCS '18). Association for Computing Machinery, New York, NY, USA, 131-145. https://doi.org/10.1145/3243734.3243736
