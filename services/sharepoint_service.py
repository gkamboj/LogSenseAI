import json

from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

from config.configuration import configs

sharepoint_base_url = 'https://sap-my.sharepoint.com/personal/gaurav_kamboj_sap_com'
sharepoint_user = configs['sharepoint.user']
sharepoint_password = configs['sharepoint.password']
# folder_in_sharepoint = '/Documents/LogSense/KBAs'

auth = AuthenticationContext(sharepoint_base_url)
token = auth.acquire_token_for_user(sharepoint_user, sharepoint_password)
if not token:
    print("Failed to acquire token")
else:
    print("Token Details:")
    print(auth.provider.token)
    access_token = auth.provider.token.get('accessToken')
    refresh_token = auth.provider.token.get('refreshToken')
    expires_in = auth.provider.token.get('expiresIn')
    expires_on = auth.provider.token.get('expiresOn')
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    print(f"Expires In: {expires_in} seconds")
    print(f"Expires On: {expires_on}")
ctx = ClientContext(sharepoint_base_url, auth)
web = ctx.web
ctx.load(web)
ctx.execute_query()
print('Connected to SharePoint: ', web.properties['Title'])


def folder_details(ctx, folder_in_sharepoint):
    folder = ctx.web.get_folder_by_server_relative_url(folder_in_sharepoint)
    fold_names = []
    sub_folders = folder.files
    ctx.load(sub_folders)
    ctx.execute_query()
    for s_folder in sub_folders:
        fold_names.append(s_folder.properties["Name"])
    return fold_names


# file_list = folder_details(ctx, folder_in_sharepoint)
# print(len(file_list))

# sharepoint_file = '/teams/SustainabilityDataAccelerator/Shared%20Documents/General/Agro/2018_indirects_sustainable_sourcing_template.xlsx'
# file_response = File.open_binary(ctx, sharepoint_file)
#
# with open("sharepointfile.csv", 'wb') as output_file:
#     output_file.write(file_response.content)
