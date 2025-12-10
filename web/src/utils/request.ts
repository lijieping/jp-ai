import type { HookFetchPlugin } from 'hook-fetch';
import { ElMessage } from 'element-plus';
import hookFetch from 'hook-fetch';
import { sseTextDecoderPlugin } from 'hook-fetch/plugins';
import router from '@/routers';
import { useUserStore } from '@/stores';

interface BaseResponse {
  code: number;
  data: never;
  msg: string;
  rows: never;
}

export const request = hookFetch.create<BaseResponse, 'data' | 'rows'>({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  plugins: [sseTextDecoderPlugin({ json: true, prefix: 'data:' })],
});

export const request4File = hookFetch.create<BaseResponse, 'data' | 'rows'>({
  baseURL: import.meta.env.VITE_API_URL,
  plugins: [sseTextDecoderPlugin({ json: true, prefix: 'data:' })],
});

function jwtPlugin(): HookFetchPlugin<BaseResponse> {
  const userStore = useUserStore();
  return {
    name: 'jwt',
    beforeRequest: async (config) => {
      //console.log("jwtPlugin before", config)
      if (userStore.token) {
        config.headers = new Headers(config.headers);
        config.headers.set('authorization', `Bearer ${userStore.token}`);
      }
      return config;
    },
    // 错误响应（4xx/5xx）会走到这里
    onError: async (error, _) => {
      const rspBody = await error.response?.json();
      // console.log("err rsp body:", rspBody)

      // 处理403逻辑
      if (error.status === 403) {
        // 跳转到403页面（确保路由已配置）
        router.replace({
          name: '403',
        });
        ElMessage.error(rspBody.detail);
        return Promise.reject(error);
      }
      // 处理401逻辑
      if (error.status === 401) {
        // 如果没有权限，退出，且弹框提示登录
        userStore.logout();
        // console.log("http 401响应")
        userStore.openLoginDialog();
        ElMessage.error(rspBody.detail);
        return Promise.reject(error);
      }
      // 其他错误
      console.log(rspBody.detail)
      ElMessage.error("系统错误");
      return Promise.reject(error);
    },
    afterResponse: async (response) => {
      //console.log("jwtPlugin after", response)
        return response;
    },
  };
}

request.use(jwtPlugin());
request4File.use(jwtPlugin());

export const post = request.post;

export const get = request.get;

export const put = request.put;

export const del = request.delete;

export const postFile = request4File.post;

export default request;
