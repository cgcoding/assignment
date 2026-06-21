#!/bin/bash

# Usage check
if [ "$#" -ne 1 ]; then
    echo "Usage: ./decipher.sh <url>"
    exit 1
fi

URL="$1"

# Full lowercase and uppercase alphabets used for Caesar cipher tr mappings
LOWER="abcdefghijklmnopqrstuvwxyz"
UPPER="ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# a. Download the encrypted letter quietly and save as encrypted.txt
wget -q "$URL" -O encrypted.txt

# b. Try all 26 possible Caesar shifts on the last line of encrypted.txt.
#    A shift of S means every letter was moved forward by S during encryption,
#    so to decrypt we shift BACK by S (= forward by 26-S).
#    We look for the shift that produces "Queen", "Majesty", "Marie", or "Mary".

LAST_LINE=$(tail -1 encrypted.txt)
FOUND_SHIFT=-1

for s in $(seq 0 25); do
    back=$((26 - s))
    # Build the decrypted alphabet for this trial shift:
    #   "${LOWER:$back}" = letters from position 'back' to end
    #   "${LOWER:0:$back}" = first 'back' letters
    # Together they form a rotation of the alphabet shifted back by s.
    shifted_lower="${LOWER:$back}${LOWER:0:$back}"
    shifted_upper="${UPPER:$back}${UPPER:0:$back}"

    decrypted=$(echo "$LAST_LINE" | tr "${LOWER}${UPPER}" "${shifted_lower}${shifted_upper}")

    if echo "$decrypted" | grep -qi "Marie\|Majesty\|Queen\|Mary"; then
        FOUND_SHIFT=$s
        break
    fi
done

# c. Having found the shift key, decipher the whole letter and save as deciphered.txt.
#    We apply the same backward rotation to every line, preserving newlines.
if [ "$FOUND_SHIFT" -ge 0 ]; then
    back=$((26 - FOUND_SHIFT))
    shifted_lower="${LOWER:$back}${LOWER:0:$back}"
    shifted_upper="${UPPER:$back}${UPPER:0:$back}"
    tr "${LOWER}${UPPER}" "${shifted_lower}${shifted_upper}" < encrypted.txt > deciphered.txt
fi

# d. Encrypt a specific plaintext with the SAME forward shift used by Mary,
#    then append it to encrypted.txt.
PLAINTEXT="I would be glad to know the names and qualities of the six gentlemen which are to accomplish the designment."

enc_lower="${LOWER:$FOUND_SHIFT}${LOWER:0:$FOUND_SHIFT}"
enc_upper="${UPPER:$FOUND_SHIFT}${UPPER:0:$FOUND_SHIFT}"
encrypted_line=$(echo "$PLAINTEXT" | tr "${LOWER}${UPPER}" "${enc_lower}${enc_upper}")

echo "$encrypted_line" >> encrypted.txt
