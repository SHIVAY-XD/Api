import axios from "axios";

const API_URL = "http://localhost:8080";
const video_url = "https://www.instagram.com/reel/C0djb2Yow4C/";

try {
  const response = await axios.get(API_URL, {
    params: { url: video_url },
  });

  console.log(response.data);
} catch (error) {
  console.error(error);
}
