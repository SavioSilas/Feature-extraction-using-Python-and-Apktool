import subprocess
import json
import os
import datetime

start_time = datetime.datetime.now()
# Path to Apk
apk_file = 'aplicativo.apk'

# Path to Apktool
apktool_path = 'apktool.jar'

# Decode the APK using Apktool
subprocess.run(['java', '-jar', apktool_path, 'd', apk_file, '-o', 'output'], check=True)

directory_generated_by_apktool = 'output'

# Extract permissions
permissions = []
with open(os.path.join(directory_generated_by_apktool, "AndroidManifest.xml"), "r") as f:
    for line in f:
        if "android.permission." in line:
            permission = line.split("android.permission.")[1].split('"')[0]
            permissions.append(permission)
print('Extracted Permissions...')

# Extract activities
activities = []
with open(os.path.join(directory_generated_by_apktool, "AndroidManifest.xml"), "r") as f:
    for line in f:
        if "<activity" in line:
            activity = line.split("android:name=\"")[1].split('"')[0]
            activities.append(activity)
print('Extracted Activities...')

# Extract intents
intents = []
with open(os.path.join(directory_generated_by_apktool, "AndroidManifest.xml"), "r") as f:
    for line in f:
        if "<intent-filter" in line:
            for subline in f:
                if "action" in subline:
                    intent = subline.split("android:name=\"")[1].split('"')[0]
                    intents.append(intent)
                    break
print('Extracted Intents...')

# Extract the apicalls and opcodes
smali_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(directory_generated_by_apktool) for f in filenames if f.endswith('.smali')]

api_candidates = ["Landroid/", "Lcom/android/internal/util", "Ldalvik/", "Ljava/", "Ljavax/", "Lorg/apache/",
                  "Lorg/json/", "Lorg/w3c/dom/", "Lorg/xml/sax", "Lorg/xmlpull/v1/", "Ljunit/"]
common_methods = ['<init>', 'equals', 'hashCode', 'toString', 'clone', 'finalize', 'wait', 'print', 'println']

opcodes = {}
api_calls = {}

for smali_file in smali_files:
    try:
        #with open(smali_file, 'r') as f:
        with open(smali_file, encoding='cp1252', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                # Extract apicalls
                if "invoke-" in line:
                    apicall_name = line.split()[-1].split('(')[0]
                    for candidate in api_candidates:
                        if apicall_name.startswith(candidate):
                            found_common_method = False
                            for common_method in common_methods:
                                if apicall_name.endswith(common_method):
                                    found_common_method = True
                                    break
                            if not found_common_method:
                                for common_method in common_methods:
                                    if common_method in apicall_name:
                                        break
                                else:
                                    apicall_name = apicall_name.replace("/", ".")
                                    apicall_name = apicall_name.replace(";", "")
                                    apicall_name = apicall_name.replace(">", ".")
                                    apicall_name = apicall_name.replace("-", "")
                                    api_calls[apicall_name] = api_calls.get(apicall_name, 0) + 1
                # Extract opcodes
                if line.startswith('    ') and not line.startswith('    .'):
                    opcode_name = line.split()[0]
                    if not any(char in opcode_name for char in ['\\', '"', '>', ';', '(', ')', '<', '}', ':', '0x']) and len(opcode_name) > 2:
                        opcodes[opcode_name] = opcodes.get(opcode_name, 0) + 1
    except IOError:
        print("Arquivo não encontrado: " + smali_file)
        # ou simplesmente ignore a exceção e continue a execução

print('Apicalls  extraidas...')
print('Opcodes extraidas...')

# Create the output dictionary
output_dict = {
    'PERMISSION': permissions,
    'INTENTS': intents,
    'ACTIVITIES': activities,
    'APICALLS': {k: v for k, v in sorted(api_calls.items(), key=lambda item: item[1], reverse=True)},
    'OPCODES': {k: v for k, v in sorted(opcodes.items(), key=lambda item: item[1], reverse=True)}
}

# Write the JSON file
with open('output.json', 'w') as f:
    json.dump(output_dict, f, indent=4)

end_time = datetime.datetime.now()
total_time = end_time - start_time
time_in_seconds = total_time.total_seconds()
time_in_hms = str(datetime.timedelta(seconds=time_in_seconds))

print("Total execution time: ", time_in_hms)