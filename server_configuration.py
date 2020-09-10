import os
import sys
sys.path.insert(1, '/root/linux_admin_script/cld_monitoring/')
import params_config
import subprocess
import boto3
from subprocess import Popen, PIPE, STDOUT
from botocore.exceptions import ClientError

region_nm=params_config.region_nm
customer_id=params_config.customer_id
ssm = boto3.client('ssm',region_name = region_nm)
envid=params_config.env_id

f = open("Response.ini", "a+")
f.write("[Server] \\nServer=1 \\nAction=2 \\n")

#server_def = subprocess.Popen(['grep','ServerInstanceName','/opt/mstr/MicroStrategy/MSIReg.reg'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
server_def = subprocess.Popen(["grep ServerInstanceName /opt/mstr/MicroStrategy/MSIReg.reg"], stdout=subprocess.PIPE, shell=True)\
out, err = server_def.communicate()

mstrpwdResp = ssm.get_parameters(Names=['/apps/'+envid+'/prov-portal/mstr'],WithDecryption=True)
mstrpwd = mstrpwdResp['Parameters'][0]['Value']

try:
  getResponse = ssm.get_parameters_by_path(Path='/database/'+envid+'/',WithDecryption=True)
  if len(getResponse.get('Parameters')) != 0:
        for params in getResponse['Parameters']:
            name = params.get('Name')
            if name.endswith('mddb'):
                dbUsrName = params.get('Name').split('/')[-1]
                dbUsrPwd = params.get('Value')
                #print dbUsrName
                #print dbUsrPwd

  else:
         print("\{\} database parameters doesn't exist in parameter store , please check".format(envid))
except ClientError as clienterr:
        message = clienterr.response['Error']['Code']
        print("Error  - \{\}".format(message))

start = out.find('"ServerInstanceName"="') + 22
end = out.find('"', start)
final = out[start:end]
f.write("InstanceName=")
f.write(final)
f.write("\\nProjectsToRegister=\\\\")
f.write("\\nProjectsToUnregister=")

'''
with open('/opt/mstr/MicroStrategy/MSIReg.reg') as msifile:
    for line in msifile:
        if line.startswith('"Location"="DSN='):
            dsn = line[16:-4]
            f.write(dsn)
'''

dsn_check_msireg='cat /opt/mstr/MicroStrategy/MSIReg.reg|grep DSN=|sed "s/.*DSN=\\(\\w\\+\\).*/\\\\1/"'

def run_command(cmd):
    try:
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        output = p.stdout.read().strip()
        return output
    except Exception as err:
        err_msg = str(err)
        print("Error :%s while running command :%s" %(err_msg,cmd))
        raise

dsn = run_command(dsn_check_msireg)

f.write("\\nDSName=")
f.write(dsn)

f.write("\\nDSNUser=")
f.write(dbUsrName)
f.write("\\nDSNPwd=")

f.write(dbUsrPwd)
f.write("\\nMDPrefix=\\nDSSUser=mstr\\nDSSPwd=")
f.write(mstrpwd)

f.write("\\nPort=34952\\nEncryptPassword=0\\nRegisterAsService=0\\nStartServerAfterConfig=1\\nConfigureSSL=0\\nSSLPort=\\nCertificatePath=\\nKeyPath=\\nKeyPassword=\\nDefaultStatisticsRep=0\\nDefaultDSNNameDefaultStatistics=\\nUserNameDefaultStatistics=\\nUserPwdDefaultStatistics=\\nEncryptUserPwdDefaultStatistics=\\nDefaultStatisticsPrefix=\\nkafkaHost(s)=\\nConfigMessagingService=0\\nKeepStatisticsSettings=0\\nRESTPort=34962")
f.close()
}
