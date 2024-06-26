import { FILES_API_URL } from '@/config';
import { logger } from '@/utils/logger';
import { getidtoken } from '@/features/auth/api';

type FileURLs = {
    upload_url: string;
    blob_url: string;
};

const get_image_upload_url = async (
    feature: 'user' | 'org' | 'event',
): Promise<FileURLs> => {
    const headers = {
        'Content-Type': 'application/json',
        id_token: await getidtoken(),
    };
    const routes = {
        user: 'get_profile_upload_url',
        org: 'get_organizations_upload_url',
        event: 'get_events_upload_url',
    };
    const res = await fetch(`${FILES_API_URL}/${routes[feature]}`, {
        method: 'GET',
        headers: headers,
    });

    const data = await res.json();
    logger(`get_image_upload_url ${feature} ${JSON.stringify(data)}`);

    if (res.status !== 200) throw res;

    const urls = {
        upload_url: data.url,
        blob_url: data['blob-url'],
    } as FileURLs;
    return urls;
};

export const upload_image = async (
    files: FileList,
    feature: 'user' | 'org' | 'event',
): Promise<string> => {
    const { upload_url, blob_url } = await get_image_upload_url(feature);
    const file = files[0];

    const headers = {
        'Content-Type': 'image/jpeg',
    };
    
    const res = await fetch(`${upload_url}`, {
        method: 'PUT',
        headers: headers,
        body: file,
    });

    console.log(res);
    const data = await res.text();
    logger(`upload_image ${feature} ${JSON.stringify(data)}`);

    if (res.status !== 200) throw res;

    return blob_url;
};
