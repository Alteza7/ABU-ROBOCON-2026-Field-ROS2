# R2MyRobot — Ringkasan Topik

Berikut keterangan singkat untuk setiap paket/tema dalam folder `r2myrobot`.

- **r2myrobot_2d** — GUI 2D (tkinter) untuk meletakkan robot, kontrol, dan integrasi visual dengan ROS topics.
- **r2myrobot_base** — Konfigurasi dasar robot (EKF, parameter sensor, file config).
- **r2myrobot_bringup** — Launch dan konfigurasi untuk menyalakan node perangkat keras dan stack robot.
- **r2myrobot_description** — URDF/xacro dan konfigurasi RViz untuk deskripsi dan visualisasi robot.
- **r2myrobot_gazebo** — Integrasi Gazebo (worlds, plugins, model meshes) untuk simulasi fisik 3D.
- **r2myrobot_navigation** — Konfigurasi navigation/SLAM (launch, param, peta, rviz presets).
- **r2myrobot_simworld** — Simulasi 2D ringan: raycast LIDAR, odom, TF, area toggles dan demo nodes.
- **r2myrobot** — Paket meta / utilitas (script helper seperti `update_microros.bash`).
- **hook/** — Script hook (packaging, CI helpers) yang terkait dengan r2myrobot paket.
- **resource/** — Aset dan resource pendukung (ikon, file tambahan).
- **test/** — Suite pengujian (unit, lint, integrasi ringan) untuk menjaga kualitas kode.
- **launch/** — Contoh launch files (lokal di tiap paket) untuk memulai demo dan komponen.
- **params/** — File YAML parameter (mis. `simworld_params.yaml`) untuk konfigurasi runtime.

Gunakan file ini sebagai panduan cepat untuk menemukan apa yang Anda butuhkan dalam workspace r2myrobot.