"""
Camera Discovery System
Discovers cameras on the network using multiple methods:
- ONVIF discovery
- RTSP probing
- Network scanning
- Reolink API discovery
"""
import logging
import socket
import subprocess
import re
from typing import List, Dict, Optional
import requests
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
import ipaddress

logger = logging.getLogger(__name__)


class CameraDiscovery:
    """Discover cameras on the network"""

    def __init__(self, timeout=2):
        """
        Initialize camera discovery

        Args:
            timeout: Timeout for network operations (seconds)
        """
        self.timeout = timeout
        self.discovered_cameras = []

    def discover_all(self, network_range: str = None) -> List[Dict]:
        """
        Discover all cameras using multiple methods

        Args:
            network_range: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            List of discovered cameras
        """
        self.discovered_cameras = []

        logger.info("Starting camera discovery...")

        # Method 1: ONVIF discovery
        onvif_cameras = self._discover_onvif()
        logger.info(f"ONVIF discovery found {len(onvif_cameras)} cameras")

        # Method 2: Network scan for common camera ports
        if network_range:
            scan_cameras = self._scan_network(network_range)
            logger.info(f"Network scan found {len(scan_cameras)} cameras")
        else:
            scan_cameras = []

        # Merge results (remove duplicates)
        all_cameras = self._merge_cameras(onvif_cameras + scan_cameras)

        # Method 3: Try to get additional info for each camera
        enriched_cameras = self._enrich_camera_info(all_cameras)

        self.discovered_cameras = enriched_cameras
        return enriched_cameras

    def discover_nvr_cameras(self, nvr_ip: str, nvr_port: int = 80,
                            username: str = '', password: str = '',
                            nvr_type: str = 'auto') -> List[Dict]:
        """
        Discover all cameras connected to an NVR

        Args:
            nvr_ip: NVR IP address
            nvr_port: NVR HTTP port (default 80)
            username: Username for authentication
            password: Password for authentication
            nvr_type: NVR type ('auto', 'reolink', 'hikvision', 'dahua', etc.)

        Returns:
            List of cameras connected to the NVR
        """
        logger.info(f"Discovering cameras on NVR {nvr_ip}:{nvr_port}")

        # Auto-detect NVR type if not specified
        if nvr_type == 'auto':
            nvr_type = self._detect_nvr_type(nvr_ip, nvr_port)
            logger.info(f"Detected NVR type: {nvr_type}")

        cameras = []

        if nvr_type == 'reolink':
            cameras = self._discover_reolink_nvr_cameras(nvr_ip, nvr_port, username, password)
        elif nvr_type == 'hikvision':
            cameras = self._discover_hikvision_nvr_cameras(nvr_ip, nvr_port, username, password)
        elif nvr_type == 'dahua':
            cameras = self._discover_dahua_nvr_cameras(nvr_ip, nvr_port, username, password)
        else:
            logger.warning(f"Unsupported NVR type: {nvr_type}")
            # Try generic ONVIF discovery as fallback
            cameras = self._discover_generic_nvr_cameras(nvr_ip, nvr_port, username, password)

        logger.info(f"Found {len(cameras)} cameras on NVR")
        return cameras

    def _detect_nvr_type(self, ip: str, port: int) -> str:
        """
        Auto-detect NVR type

        Args:
            ip: NVR IP address
            port: NVR port

        Returns:
            NVR type string
        """
        try:
            url = f"http://{ip}:{port}"
            response = requests.get(url, timeout=self.timeout, verify=False)

            content = response.text.lower()
            headers = {k.lower(): v for k, v in response.headers.items()}

            if 'reolink' in content or 'reolink' in headers.get('server', ''):
                return 'reolink'
            elif 'hikvision' in content or 'hikvision' in headers.get('server', ''):
                return 'hikvision'
            elif 'dahua' in content:
                return 'dahua'

        except Exception as e:
            logger.debug(f"NVR type detection failed: {e}")

        return 'generic'

    def _discover_reolink_nvr_cameras(self, ip: str, port: int, username: str, password: str) -> List[Dict]:
        """
        Discover cameras on a Reolink NVR

        Args:
            ip: NVR IP address
            port: NVR port
            username: Username
            password: Password

        Returns:
            List of cameras
        """
        cameras = []

        try:
            # Get channel info from Reolink NVR API
            url = f"http://{ip}:{port}/api.cgi?cmd=GetChannelStatus"

            if username and password:
                response = requests.get(url, auth=(username, password), timeout=5, verify=False)
            else:
                response = requests.get(url, timeout=5, verify=False)

            if response.status_code == 200:
                data = response.json()

                if 'value' in data and 'ChannelStatus' in data['value']:
                    channels = data['value']['ChannelStatus']

                    for channel in channels:
                        channel_id = channel.get('channel', 0)
                        channel_name = channel.get('name', f'Channel {channel_id}')
                        online = channel.get('online', 0) == 1

                        if online:
                            # Generate RTSP URLs for this channel
                            camera = {
                                'ip': ip,
                                'port': 554,
                                'protocol': 'reolink_nvr',
                                'nvr_ip': ip,
                                'nvr_port': port,
                                'channel': channel_id,
                                'name': f"{channel_name} (NVR {ip} Ch{channel_id})",
                                'manufacturer': 'Reolink',
                                'model': 'NVR Channel',
                                'online': online,
                                'rtsp_urls': [
                                    {
                                        'name': 'Main Stream',
                                        'url': f"rtsp://{ip}:554/h264Preview_{channel_id:02d}_main",
                                        'quality': 'high'
                                    },
                                    {
                                        'name': 'Sub Stream',
                                        'url': f"rtsp://{ip}:554/h264Preview_{channel_id:02d}_sub",
                                        'quality': 'low'
                                    }
                                ],
                                'capabilities': {
                                    'rtsp': True,
                                    'nvr_channel': True
                                }
                            }
                            cameras.append(camera)

            # Also try to get device info
            url = f"http://{ip}:{port}/api.cgi?cmd=GetDevInfo"
            if username and password:
                response = requests.get(url, auth=(username, password), timeout=5, verify=False)
            else:
                response = requests.get(url, timeout=5, verify=False)

            if response.status_code == 200:
                dev_info = response.json()
                if 'value' in dev_info and 'DevInfo' in dev_info['value']:
                    nvr_model = dev_info['value']['DevInfo'].get('model', 'NVR')
                    # Update camera info with NVR model
                    for camera in cameras:
                        camera['nvr_model'] = nvr_model

        except Exception as e:
            logger.error(f"Failed to discover Reolink NVR cameras: {e}")

        return cameras

    def _discover_hikvision_nvr_cameras(self, ip: str, port: int, username: str, password: str) -> List[Dict]:
        """
        Discover cameras on a Hikvision NVR

        Args:
            ip: NVR IP address
            port: NVR port
            username: Username
            password: Password

        Returns:
            List of cameras
        """
        cameras = []

        try:
            # Hikvision uses ISAPI
            url = f"http://{ip}:{port}/ISAPI/System/Video/inputs/channels"

            if username and password:
                response = requests.get(url, auth=(username, password), timeout=5, verify=False)
            else:
                response = requests.get(url, timeout=5, verify=False)

            if response.status_code == 200:
                # Parse XML response
                root = ET.fromstring(response.content)

                for video_input in root.findall('.//VideoInputChannel'):
                    channel_id = video_input.find('id')
                    channel_name = video_input.find('name')

                    if channel_id is not None:
                        ch_id = int(channel_id.text)
                        ch_name = channel_name.text if channel_name is not None else f'Channel {ch_id}'

                        camera = {
                            'ip': ip,
                            'port': 554,
                            'protocol': 'hikvision_nvr',
                            'nvr_ip': ip,
                            'nvr_port': port,
                            'channel': ch_id,
                            'name': f"{ch_name} (Hikvision NVR {ip} Ch{ch_id})",
                            'manufacturer': 'Hikvision',
                            'model': 'NVR Channel',
                            'rtsp_urls': [
                                {
                                    'name': 'Main Stream',
                                    'url': f"rtsp://{ip}:554/Streaming/Channels/{ch_id}01",
                                    'quality': 'high'
                                },
                                {
                                    'name': 'Sub Stream',
                                    'url': f"rtsp://{ip}:554/Streaming/Channels/{ch_id}02",
                                    'quality': 'low'
                                }
                            ],
                            'capabilities': {
                                'rtsp': True,
                                'nvr_channel': True
                            }
                        }
                        cameras.append(camera)

        except Exception as e:
            logger.error(f"Failed to discover Hikvision NVR cameras: {e}")

        return cameras

    def _discover_dahua_nvr_cameras(self, ip: str, port: int, username: str, password: str) -> List[Dict]:
        """
        Discover cameras on a Dahua NVR

        Args:
            ip: NVR IP address
            port: NVR port
            username: Username
            password: Password

        Returns:
            List of cameras
        """
        cameras = []

        try:
            # Dahua uses CGI API
            # Try to get channel count
            url = f"http://{ip}:{port}/cgi-bin/magicBox.cgi?action=getProductDefinition"

            if username and password:
                response = requests.get(url, auth=(username, password), timeout=5, verify=False)
            else:
                response = requests.get(url, timeout=5, verify=False)

            if response.status_code == 200:
                content = response.text

                # Parse channel count
                channel_count = 16  # Default assumption
                match = re.search(r'VideoInChannel=(\d+)', content)
                if match:
                    channel_count = int(match.group(1))

                # Create cameras for each channel
                for ch_id in range(1, channel_count + 1):
                    camera = {
                        'ip': ip,
                        'port': 554,
                        'protocol': 'dahua_nvr',
                        'nvr_ip': ip,
                        'nvr_port': port,
                        'channel': ch_id,
                        'name': f"Channel {ch_id} (Dahua NVR {ip})",
                        'manufacturer': 'Dahua',
                        'model': 'NVR Channel',
                        'rtsp_urls': [
                            {
                                'name': 'Main Stream',
                                'url': f"rtsp://{ip}:554/cam/realmonitor?channel={ch_id}&subtype=0",
                                'quality': 'high'
                            },
                            {
                                'name': 'Sub Stream',
                                'url': f"rtsp://{ip}:554/cam/realmonitor?channel={ch_id}&subtype=1",
                                'quality': 'low'
                            }
                        ],
                        'capabilities': {
                            'rtsp': True,
                            'nvr_channel': True
                        }
                    }
                    cameras.append(camera)

        except Exception as e:
            logger.error(f"Failed to discover Dahua NVR cameras: {e}")

        return cameras

    def _discover_generic_nvr_cameras(self, ip: str, port: int, username: str, password: str) -> List[Dict]:
        """
        Try to discover cameras on a generic NVR using ONVIF

        Args:
            ip: NVR IP address
            port: NVR port
            username: Username
            password: Password

        Returns:
            List of cameras
        """
        cameras = []

        try:
            # Try ONVIF for generic NVRs
            from onvif import ONVIFCamera

            mycam = ONVIFCamera(ip, port, username, password)

            # Get media service
            media_service = mycam.create_media_service()
            profiles = media_service.GetProfiles()

            for idx, profile in enumerate(profiles):
                camera = {
                    'ip': ip,
                    'port': 554,
                    'protocol': 'onvif_nvr',
                    'nvr_ip': ip,
                    'nvr_port': port,
                    'channel': idx + 1,
                    'name': f"ONVIF Profile {idx + 1} (NVR {ip})",
                    'manufacturer': 'Generic',
                    'model': 'NVR Channel',
                    'profile_token': profile.token,
                    'capabilities': {
                        'onvif': True,
                        'nvr_channel': True
                    }
                }

                # Try to get stream URI
                try:
                    stream_uri = media_service.GetStreamUri({
                        'StreamSetup': {'Stream': 'RTP-Unicast', 'Transport': {'Protocol': 'RTSP'}},
                        'ProfileToken': profile.token
                    })

                    if stream_uri and hasattr(stream_uri, 'Uri'):
                        camera['rtsp_urls'] = [
                            {'name': f'Profile {idx + 1}', 'url': stream_uri.Uri, 'quality': 'high'}
                        ]

                except Exception as e:
                    logger.debug(f"Failed to get stream URI: {e}")

                cameras.append(camera)

        except ImportError:
            logger.warning("python-onvif-zeep not installed, cannot use ONVIF for generic NVR")
        except Exception as e:
            logger.error(f"Failed to discover generic NVR cameras: {e}")

        return cameras

    def _discover_onvif(self) -> List[Dict]:
        """
        Discover ONVIF cameras using WS-Discovery

        Returns:
            List of ONVIF cameras
        """
        cameras = []

        try:
            # Try to use onvif-zeep if available
            try:
                from onvif import ONVIFCamera
                from wsdiscovery.discovery import ThreadedWSDiscovery as WSDiscovery

                wsd = WSDiscovery()
                wsd.start()
                services = wsd.searchServices()
                wsd.stop()

                for service in services:
                    if 'onvif' in str(service.getTypes()).lower():
                        # Extract IP from XAddrs
                        xaddrs = service.getXAddrs()
                        if xaddrs:
                            ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', xaddrs[0])
                            if ip_match:
                                ip = ip_match.group(1)
                                cameras.append({
                                    'ip': ip,
                                    'port': 80,
                                    'protocol': 'onvif',
                                    'name': f"ONVIF Camera {ip}",
                                    'manufacturer': 'Unknown',
                                    'model': 'Unknown',
                                    'onvif_service': xaddrs[0]
                                })

            except ImportError:
                logger.warning("onvif-zeep not installed, skipping ONVIF discovery")

        except Exception as e:
            logger.error(f"ONVIF discovery failed: {e}")

        return cameras

    def _scan_network(self, network_range: str) -> List[Dict]:
        """
        Scan network for cameras on common ports

        Args:
            network_range: Network range (e.g., "192.168.1.0/24")

        Returns:
            List of discovered cameras
        """
        cameras = []
        common_ports = [554, 80, 8000, 8080, 8554, 9000]  # RTSP, HTTP, common camera ports

        try:
            network = ipaddress.ip_network(network_range, strict=False)
            hosts = list(network.hosts())

            logger.info(f"Scanning {len(hosts)} hosts on {network_range}")

            # Limit to reasonable subnet size
            if len(hosts) > 254:
                logger.warning(f"Network too large ({len(hosts)} hosts), limiting to first 254")
                hosts = hosts[:254]

            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = []
                for host in hosts:
                    for port in common_ports:
                        futures.append(executor.submit(self._probe_camera, str(host), port))

                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        cameras.append(result)

        except Exception as e:
            logger.error(f"Network scan failed: {e}")

        return cameras

    def _probe_camera(self, ip: str, port: int) -> Optional[Dict]:
        """
        Probe a specific IP:port for camera services

        Args:
            ip: IP address
            port: Port number

        Returns:
            Camera info if found, None otherwise
        """
        try:
            # Try to connect
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()

            if result == 0:
                # Port is open, try to identify service
                protocol = 'unknown'
                name = f"Camera {ip}:{port}"

                if port == 554 or port == 8554:
                    # Likely RTSP
                    if self._test_rtsp(ip, port):
                        protocol = 'rtsp'
                        name = f"RTSP Camera {ip}"

                elif port in [80, 8000, 8080, 9000]:
                    # Likely HTTP/Web interface
                    camera_info = self._probe_http_camera(ip, port)
                    if camera_info:
                        return camera_info

                if protocol != 'unknown':
                    return {
                        'ip': ip,
                        'port': port,
                        'protocol': protocol,
                        'name': name,
                        'manufacturer': 'Unknown',
                        'model': 'Unknown'
                    }

        except Exception:
            pass

        return None

    def _test_rtsp(self, ip: str, port: int) -> bool:
        """
        Test if RTSP service is available

        Args:
            ip: IP address
            port: Port number

        Returns:
            True if RTSP service responds
        """
        try:
            # Try RTSP OPTIONS request
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))

            request = f"OPTIONS rtsp://{ip}:{port}/ RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            sock.send(request.encode())

            response = sock.recv(1024).decode()
            sock.close()

            return 'RTSP/1.0' in response or 'RTSP/2.0' in response

        except Exception:
            return False

    def _probe_http_camera(self, ip: str, port: int) -> Optional[Dict]:
        """
        Probe HTTP port for camera web interface

        Args:
            ip: IP address
            port: Port number

        Returns:
            Camera info if camera detected
        """
        try:
            url = f"http://{ip}:{port}"
            response = requests.get(url, timeout=self.timeout, verify=False)

            # Check for camera-specific headers or content
            content = response.text.lower()
            headers = {k.lower(): v for k, v in response.headers.items()}

            manufacturer = 'Unknown'
            model = 'Unknown'
            protocol = 'http'

            # Detect Reolink
            if 'reolink' in content or 'reolink' in headers.get('server', ''):
                manufacturer = 'Reolink'
                protocol = 'reolink'
                model = self._detect_reolink_model(ip, port)

            # Detect Hikvision
            elif 'hikvision' in content or 'hikvision' in headers.get('server', ''):
                manufacturer = 'Hikvision'
                model = 'Camera'

            # Detect Dahua
            elif 'dahua' in content:
                manufacturer = 'Dahua'
                model = 'Camera'

            # Detect Axis
            elif 'axis' in content or 'axis' in headers.get('server', ''):
                manufacturer = 'Axis'
                model = 'Camera'

            # Detect Ubiquiti/UniFi
            elif 'ubiquiti' in content or 'unifi' in content:
                manufacturer = 'Ubiquiti'
                model = 'UniFi Camera'

            # Generic camera detection
            elif any(keyword in content for keyword in ['camera', 'ipcam', 'webcam', 'surveillance']):
                manufacturer = 'Generic'
                model = 'IP Camera'
            else:
                # Not a camera
                return None

            return {
                'ip': ip,
                'port': port,
                'protocol': protocol,
                'name': f"{manufacturer} {model} ({ip})",
                'manufacturer': manufacturer,
                'model': model,
                'web_interface': url
            }

        except Exception:
            return None

    def _detect_reolink_model(self, ip: str, port: int) -> str:
        """
        Try to detect Reolink camera model

        Args:
            ip: IP address
            port: Port number

        Returns:
            Model name
        """
        try:
            # Try Reolink API
            url = f"http://{ip}:{port}/api.cgi?cmd=GetDevInfo"
            response = requests.get(url, timeout=self.timeout, verify=False)

            if response.status_code == 200:
                data = response.json()
                if 'value' in data and 'DevInfo' in data['value']:
                    return data['value']['DevInfo'].get('model', 'Camera')

        except Exception:
            pass

        return 'Camera'

    def _merge_cameras(self, cameras: List[Dict]) -> List[Dict]:
        """
        Merge duplicate camera entries

        Args:
            cameras: List of camera dictionaries

        Returns:
            Deduplicated list
        """
        unique = {}

        for cam in cameras:
            key = f"{cam['ip']}:{cam['port']}"

            if key not in unique:
                unique[key] = cam
            else:
                # Merge info (prefer more specific data)
                existing = unique[key]
                if cam.get('manufacturer') != 'Unknown':
                    existing['manufacturer'] = cam['manufacturer']
                if cam.get('model') != 'Unknown':
                    existing['model'] = cam['model']
                if 'web_interface' in cam:
                    existing['web_interface'] = cam['web_interface']
                if 'onvif_service' in cam:
                    existing['onvif_service'] = cam['onvif_service']

        return list(unique.values())

    def _enrich_camera_info(self, cameras: List[Dict]) -> List[Dict]:
        """
        Try to get additional information for each camera

        Args:
            cameras: List of camera dictionaries

        Returns:
            Enriched camera list
        """
        enriched = []

        for cam in cameras:
            # Try to get RTSP URLs
            if cam['protocol'] in ['rtsp', 'reolink', 'onvif']:
                cam['rtsp_urls'] = self._guess_rtsp_urls(cam)

            # Try to get capabilities
            cam['capabilities'] = self._get_camera_capabilities(cam)

            enriched.append(cam)

        return enriched

    def _guess_rtsp_urls(self, camera: Dict) -> List[Dict]:
        """
        Generate likely RTSP URLs for camera

        Args:
            camera: Camera dictionary

        Returns:
            List of RTSP URL patterns
        """
        ip = camera['ip']
        manufacturer = camera['manufacturer'].lower()

        rtsp_patterns = []

        if manufacturer == 'reolink':
            rtsp_patterns = [
                {'name': 'Main Stream', 'url': f"rtsp://{ip}:554/h264Preview_01_main", 'quality': 'high'},
                {'name': 'Sub Stream', 'url': f"rtsp://{ip}:554/h264Preview_01_sub", 'quality': 'low'},
            ]

        elif manufacturer == 'hikvision':
            rtsp_patterns = [
                {'name': 'Main Stream', 'url': f"rtsp://{ip}:554/Streaming/Channels/101", 'quality': 'high'},
                {'name': 'Sub Stream', 'url': f"rtsp://{ip}:554/Streaming/Channels/102", 'quality': 'low'},
            ]

        elif manufacturer == 'dahua':
            rtsp_patterns = [
                {'name': 'Main Stream', 'url': f"rtsp://{ip}:554/cam/realmonitor?channel=1&subtype=0", 'quality': 'high'},
                {'name': 'Sub Stream', 'url': f"rtsp://{ip}:554/cam/realmonitor?channel=1&subtype=1", 'quality': 'low'},
            ]

        elif manufacturer == 'axis':
            rtsp_patterns = [
                {'name': 'Default', 'url': f"rtsp://{ip}:554/axis-media/media.amp", 'quality': 'high'},
            ]

        else:
            # Generic RTSP URLs
            rtsp_patterns = [
                {'name': 'Generic Main', 'url': f"rtsp://{ip}:554/", 'quality': 'high'},
                {'name': 'Generic Stream 1', 'url': f"rtsp://{ip}:554/stream1", 'quality': 'high'},
                {'name': 'Generic Live', 'url': f"rtsp://{ip}:554/live", 'quality': 'high'},
            ]

        return rtsp_patterns

    def _get_camera_capabilities(self, camera: Dict) -> Dict:
        """
        Try to determine camera capabilities

        Args:
            camera: Camera dictionary

        Returns:
            Dictionary of capabilities
        """
        capabilities = {
            'pan_tilt': False,
            'zoom': False,
            'audio': False,
            'motion_detection': False,
            'night_vision': False,
            'two_way_audio': False,
            'onvif': camera['protocol'] == 'onvif',
            'rtsp': camera['protocol'] in ['rtsp', 'reolink', 'onvif'],
            'web_interface': 'web_interface' in camera
        }

        # Try to get more info via API
        manufacturer = camera['manufacturer'].lower()

        if manufacturer == 'reolink':
            capabilities.update(self._get_reolink_capabilities(camera))

        return capabilities

    def _get_reolink_capabilities(self, camera: Dict) -> Dict:
        """
        Get capabilities for Reolink camera

        Args:
            camera: Camera dictionary

        Returns:
            Capabilities dictionary
        """
        capabilities = {}

        try:
            url = f"http://{camera['ip']}:{camera.get('port', 80)}/api.cgi?cmd=GetAbility"
            response = requests.get(url, timeout=self.timeout, verify=False)

            if response.status_code == 200:
                data = response.json()
                if 'value' in data and 'Ability' in data['value']:
                    ability = data['value']['Ability']
                    capabilities['pan_tilt'] = ability.get('ptzCtrl', {}).get('ver', 0) > 0
                    capabilities['zoom'] = ability.get('zoom', {}).get('ver', 0) > 0
                    capabilities['audio'] = ability.get('audioAlarm', {}).get('ver', 0) > 0

        except Exception as e:
            logger.debug(f"Failed to get Reolink capabilities: {e}")

        return capabilities

    def test_rtsp_stream(self, rtsp_url: str, username: str = '', password: str = '') -> bool:
        """
        Test if RTSP stream is accessible

        Args:
            rtsp_url: RTSP URL
            username: Username for authentication
            password: Password for authentication

        Returns:
            True if stream is accessible
        """
        try:
            import cv2

            # Build authenticated URL
            if username and password:
                # Insert credentials into URL
                if '://' in rtsp_url:
                    protocol, rest = rtsp_url.split('://', 1)
                    rtsp_url = f"{protocol}://{username}:{password}@{rest}"

            # Try to open stream
            cap = cv2.VideoCapture(rtsp_url)
            success = cap.isOpened()
            cap.release()

            return success

        except Exception as e:
            logger.error(f"RTSP test failed: {e}")
            return False

    def get_network_interfaces(self) -> List[Dict]:
        """
        Get list of network interfaces and their subnets

        Returns:
            List of network interfaces
        """
        interfaces = []

        try:
            import netifaces

            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)

                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr.get('addr')
                        netmask = addr.get('netmask')

                        if ip and netmask and not ip.startswith('127.'):
                            # Calculate network
                            network = ipaddress.IPv4Network(f"{ip}/{netmask}", strict=False)

                            interfaces.append({
                                'name': iface,
                                'ip': ip,
                                'netmask': netmask,
                                'network': str(network),
                                'cidr': f"{network.network_address}/{network.prefixlen}"
                            })

        except ImportError:
            logger.warning("netifaces not installed, cannot detect network interfaces")

            # Fallback: try to get local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
                s.close()

                # Assume /24 subnet
                network = ipaddress.IPv4Network(f"{local_ip}/24", strict=False)

                interfaces.append({
                    'name': 'default',
                    'ip': local_ip,
                    'netmask': '255.255.255.0',
                    'network': str(network),
                    'cidr': f"{network.network_address}/24"
                })

            except Exception as e:
                logger.error(f"Failed to get local IP: {e}")

        return interfaces
