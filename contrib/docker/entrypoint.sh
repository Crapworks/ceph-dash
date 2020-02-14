#!/usr/bin/env sh

CEPHCONFIG="/etc/ceph/ceph.conf"
CEPHKEYRING="/etc/ceph/keyring"

echo "# REQUIRED ENVIRONMENT VARIABLES"
echo "* CEPHMONS (comma separated list of ceph monitor ip addresses)"
echo "* KEYRING (full keyring to deploy in docker container)"
echo "* Or KEYRING_FILE (path to file containing keyring to deploy in docker container)"
echo ""
echo "# OPTIONAL ENVIRONMENT VARIABLES"
echo "* CONFIG (path to ceph-dash config file"
echo "* NAME (keyring name to use)"
echo "* ID (keyting id to use)"
echo ""

CEPHMONS=$(echo ${CEPHMONS} | sed 's/[a-z]\+=//g')
CEPHMONS=$(echo ${CEPHMONS} | sed 's/rook-ceph-mon[0-9]\+=//g')

echo -e "[global]\nmon host = ${CEPHMONS}" > ${CEPHCONFIG}

echo "# CEPH STATUS"
ceph -s

export CEPHDASH_CEPHCONFIG="${CEPHCONFIG}"
export CEPHDASH_KEYRING="${CEPHKEYRING}"

if [ -n "${KEYRING_FILE}" ]; then
    cat ${KEYRING_FILE} > ${CEPHKEYRING}
else
    echo "${KEYRING}" > ${CEPHKEYRING}
fi

if [ -n "${CONFIG}" ]; then
    export CEPHDASH_CONFIGFILE="${CONFIG}"
fi

if [ -n "${NAME}" ]; then
    export CEPHDASH_NAME="${NAME}"
fi

if [ -n "${ID}" ]; then
    export CEPHDASH_ID="${ID}"
fi

python $*
