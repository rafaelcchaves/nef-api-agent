Vagrant.configure("2") do |config|

  config.vm.box = "generic/ubuntu2204"
  config.vm.provider :virtualbox do |vb|
    vb.memory = "4096"
    vb.cpus = 2
  end
  
  config.vm.define "free5gc" do |free5gc|
    free5gc.vm.hostname = "free5gc"
    free5gc.vm.network :private_network, ip: "192.168.56.101"
    config.vm.network "forwarded_port", guest: 5000, host:5000
    config.vm.synced_folder "./", "/src/", owner: "vagrant", group: "vagrant", type: "rsync"
  end
end

